import json
import regex

from decimal import Decimal

QOFP_REGEX = regex.compile("^QOFP::(?P<type>[A-Za-z]+):(?P<json>.+)$")

class QofpBase:

    def __init__(self, type):

        self._type = type
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def render(self):

        return "QOFP::{type}:{json}".format(type=self._type, json=json.dumps(self._data))

    def __str__(self):

        return self.render()

class QofpPayment(QofpBase):

    def __init__(self, status=None, txHash=None, value=None, fromAddress=None, toAddress=None):

        super().__init__("Payment")

        self['status'] = status
        self['txHash'] = txHash
        self['value'] = value
        self['fromAddress'] = fromAddress
        self['toAddress'] = toAddress

    def __setitem__(self, key, value):

        if key not in ('status', 'txHash', 'value', 'tx_hash', 'hash', 'fromAddress', 'toAddress'):
            raise KeyError(key)
        if key == 'tx_hash' or key == 'hash':
            key = 'txHash'
        if key == 'value' and isinstance(value, (int, float, Decimal)):
            value = hex(value)

        return super().__setitem__(key, value)

    @classmethod
    def from_transaction(cls, tx):
        """converts a dictionary with transaction data as returned by a
        ethereum node into a qofp payment message"""

        if isinstance(tx, dict):
            if 'error' in tx:
                status = "error"
            elif tx['blockNumber'] is None:
                status = "unconfirmed"
            else:
                status = "confirmed"
            return QofpPayment(value=tx['value'], txHash=tx['hash'], status=status,
                               fromAddress=tx['from'], toAddress=tx['to'])
        else:
            raise TypeError("Unable to create QOFP::Payment from type '{}'".format(type(tx)))


VALID_QOFP_TYPES = ('message', 'command', 'init', 'initrequest', 'payment', 'paymentrequest')
IMPLEMENTED_QOFP_TYPES = {
    'payment': QofpPayment
}

def parse_qofp_message(message):

    match = QOFP_REGEX.match(message)
    if not match:
        raise SyntaxError("Invalid QOFP message")
    body = match.group('json')
    try:
        body = json.loads(body)
    except json.JSONDecodeError:
        raise SyntaxError("Invalid QOFP message: body is not valid json")

    type = match.group('type').lower()
    if type not in VALID_QOFP_TYPES:
        raise SyntaxError("Invalid QOFP type")

    if type not in IMPLEMENTED_QOFP_TYPES:
        raise NotImplementedError("QOFP type '{}' has not been implemented yet".format(match.group('type')))

    try:
        return IMPLEMENTED_QOFP_TYPES[type](**body)
    except TypeError:
        raise SyntaxError("Invalid QOFP message: body contains unexpected fields")
