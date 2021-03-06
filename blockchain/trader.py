from web3 import Web3
from eth_account import Account
import json
import datetime


class Trader:
    def __init__(self):
        # Load config files
        with open('./config.json') as f:
            self.config = json.load(f)
        with open('./pancakeswap_abi.json') as f:
            self.pancakeswap_abi = json.load(f)

        # Connect to BSC node
        self.w3 = Web3(Web3.WebsocketProvider(
            'wss://silent-old-pine.bsc.quiknode.pro/50d141387da957f5bd76a5018ec2fd33a7c48dfe/'))

        # Pancakeswap Router Address
        self.pancakeswapAddress = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
        self.pancake_contract = self.w3.eth.contract(
            address=self.pancakeswapAddress, abi=self.pancakeswap_abi)

        # Read wallet private key
        self.account = Account.from_key(config["PRIVATE_KEY"])

        # Chain ID of Binance Smart Chain mainnet
        self.chainId = "0x38"

        self.bnb_address = Web3.toChecksumAddress(
            "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")
        self.gasLimit = 4000000

    def swapExactETHForTokens(self, toTokenAddress, transferAmountInBNB, gasPriceGwei=5, max_slippage=5, minutesDeadline=5, actually_send_trade=False, verbose=False):
        # Convert BNB to BNB-Wei
        transferAmount = Web3.toWei(transferAmountInBNB, "ether")
        # Ensure address is properly formatted
        toToken = Web3.toChecksumAddress(toTokenAddress)

        # Determine the nonce
        count = self.w3.eth.getTransactionCount(self.account.address)
        if verbose:
            print("Nonce: ", count)

        # Get BNB balance
        balance = self.w3.eth.getBalance(self.account.address)
        if verbose:
            print(
                f"Balance before send: {balance} Gwei BNB\n------------------------")

        if balance < transferAmount:
            raise Exception(
                "Requested swap value is greater than the account balance. Will not execute this trade.")

        # Find the expected output amount of the destination token
        amountsOut = self.pancake_contract.functions.getAmountsOut(
            transferAmount, [self.bnb_address, toToken]).call()
        amountOutMin = amountsOut[1] * (100 - max_slippage) / 100

        # Arbitrary deadline, can tighten to reject txs if we fail to front-run?
        deadline = datetime.datetime.now(
            datetime.timezone.utc).timestamp() + (minutesDeadline * 60)

        # Fill ABI data payload with parameters:
        # swapExactETHForTokens(uint256 amountOutMin, address[] path, address to, uint256 deadline)
        swap_abi = self.pancake_contract.encodeABI('swapExactETHForTokens',
                                                   args=[int(amountOutMin), [self.bnb_address, toToken], self.account.address, int(deadline)])

        # Fill in ABI & remaining transaction details
        rawTransaction = {
            "from": self.account.address,
            "to": self.pancakeswapAddress,
            "nonce": Web3.toHex(count),
            "gasPrice": Web3.toHex(int(gasPriceGwei * 1e9)),
            "gas": Web3.toHex(self.gasLimit),
            "data": swap_abi,
            "chainId": self.chainId,
            "value": Web3.toHex(transferAmount)
        }

        if verbose:
            print(
                f"Raw of Transaction: \n${rawTransaction}\n------------------------")

        signedTx = self.w3.eth.account.sign_transaction(
            rawTransaction, self.config["PRIVATE_KEY"])

        txn_receipt = "NotExecuted"
        """
        <DANGER -- ACTUALLY EXECUTE THE SWAP>
        """
        if actually_send_trade:
            deploy_txn = self.w3.eth.send_raw_transaction(
                signedTx.rawTransaction)
            txn_receipt = self.w3.eth.wait_for_transaction_receipt(deploy_txn)
            if verbose:
                print(txn_receipt)
        """
            </DANGER>
        """

        return txn_receipt

    def swapExactTokensForETH(fromTokenAddress, transferAmountPercentage=1.0, minutesDeadline=5, max_slippage=5, actually_send_trade=False):
        # Ensure address is properly formatted
        fromToken = Web3.toChecksumAddress(fromToken)

        # Determine the nonce
        count = self.w3.eth.getTransactionCount(self.account.address)
        if verbose:
            print("Nonce: ", count)

        # Get fromToken balance
        balance_check_abi = [{
            "constant": true,
            "inputs": [
                {
                    "name": "_owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": false,
            "type": "function"
        }]

        balance_check_contract = self.w3.eth.contract(
            address=fromToken, abi=balance_check_abi)

        balance = balance_check_contract.functions.balanceOf(fromToken).call()

        if verbose:
            print(
                f"Balance before send: {balance} Gwei Shitcoin\n------------------------")

        # Determine percentage of position to exit
        transferAmount = transferAmountPercentage * balance

        if balance < transferAmount:
            raise Exception(
                "Requested swap value is greater than the account balance. Will not execute this trade.")

        # Find the expected output amount of the destination token
        amountsOut = self.pancake_contract.functions.getAmountsOut(
            transferAmount, [self.bnb_address, toToken]).call()
        amountOutMin = amountsOut[1] * (100 - max_slippage) / 100

        # Arbitrary deadline, can tighten to reject txs if we fail to front-run?
        deadline = datetime.datetime.now(
            datetime.timezone.utc).timestamp() + (minutesDeadline * 60)

        # Fill ABI data payload with parameters:
        # swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, address[] path, address to, uint256 deadline)
        swap_abi = self.pancake_contract.encodeABI('swapExactTokensForETH',
                                                   args=[int(transferAmount), int(amountOutMin), [fromToken, self.bnb_address], self.account.address, int(deadline)])

        # Fill in ABI & remaining transaction details
        rawTransaction = {
            "from": self.account.address,
            "to": self.pancakeswapAddress,
            "nonce": Web3.toHex(count),
            "gasPrice": Web3.toHex(int(gasPriceGwei * 1e9)),
            "gas": Web3.toHex(self.gasLimit),
            "data": swap_abi,
            "chainId": self.chainId,
            "value": "0x0"
        }

        if verbose:
            print(
                f"Raw of Transaction: \n${rawTransaction}\n------------------------")

        signedTx = self.w3.eth.account.sign_transaction(
            rawTransaction, self.config["PRIVATE_KEY"])

        txn_receipt = "NotExecuted"
        """
        <DANGER -- ACTUALLY EXECUTE THE SWAP>
        """
        if actually_send_trade:
            deploy_txn = self.w3.eth.send_raw_transaction(
                signedTx.rawTransaction)
            txn_receipt = self.w3.eth.wait_for_transaction_receipt(deploy_txn)
            if verbose:
                print(txn_receipt)
        """
            </DANGER>
        """

        return txn_receipt
