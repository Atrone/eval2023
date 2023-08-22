import './polyfill'; // Ensure this is imported before any other module that might use Buffer
import React, { useState, useEffect } from 'react';
import CreatableSelect from 'react-select/creatable';
import ECPairFactory from 'ecpair';
import * as ecc from 'tiny-secp256k1';
import './App.scss';
import './Transaction.scss';
import PropTypes from 'prop-types';
const bitcoin = require('bitcoinjs-lib');
const ECPair = ECPairFactory(ecc);

const TESTNET = bitcoin.networks.testnet;


const CustomOption = (props) => {
    const handleDetailsClick = (e) => {
        e.preventDefault();
        e.stopPropagation();

        const url = `/path-to-details/${props.data.value}/`;
        window.open(url, '_blank');
    };

    return (
        <div {...props.innerProps} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span onClick={() => props.selectOption(props.option)}>{props.label}</span>
            <button onClick={handleDetailsClick} style={{ marginLeft: '10px' }}>Details</button>
        </div>
    );
};

CustomOption.propTypes = {
    data: PropTypes.shape({
        value: PropTypes.string.isRequired
    }).isRequired,
    innerProps: PropTypes.object,
    selectOption: PropTypes.func.isRequired,
    option: PropTypes.object,
    label: PropTypes.string.isRequired
};


function AddressDropdown({ placeholder, fetchEndpoint, createEndpoint, onAddressChange: onAddressChangeProp }) {
    const [options, setOptions] = useState([]);

    useEffect(() => {
        fetch(fetchEndpoint)
            .then(response => response.json())
            .then(data => setOptions(data.map(item => ({ label: item.address, value: item.address }))));
    }, [fetchEndpoint]);

    const handleCreateOption = (inputValue) => {
        fetch(createEndpoint, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ address: inputValue })
        })
        .then(response => response.json())
        .then(data => {
                if (data.success) {
                    setOptions(prevOptions => [...prevOptions, { label: inputValue, value: inputValue }]);
                }
                else
                {
                    alert("Could not add address to DB (is it valid?)")
                }
        });
    };

    return (
        <CreatableSelect
            options={options}
            placeholder={placeholder}
            onChange={(selectedOption) => {
                onAddressChangeProp(selectedOption ? selectedOption.value : '');
            }}
            onCreateOption={handleCreateOption}  // Add this prop
            isClearable
            name={placeholder.toLowerCase().replace(" ", "")}
            components={{
                Option: CustomOption
            }}
        />
    );
}
AddressDropdown.propTypes = {
    placeholder: PropTypes.string.isRequired,
    fetchEndpoint: PropTypes.string.isRequired,
    createEndpoint: PropTypes.string.isRequired,
    onAddressChange: PropTypes.func.isRequired
};


function BitcoinTransaction() {
    const [toAddress, setToAddress] = useState('');
    const [fromAddress, setFromAddress] = useState('');
    const [loading, setLoading] = useState(false);

    const isValidAddress = address => {
        try {
            bitcoin.address.toOutputScript(address, TESTNET); // Decode address for testnet
            return true;
        } catch (e) {
            console.error(e);
            return false;
        }
    };

    const isValidPrivateKey = key => {
        try {
            ECPair.fromWIF(key, TESTNET);
            return true;
        } catch (e) {
            console.error(e);
            return false;
        }
    };

    const isValidAmount = amt => {
        return !isNaN(amt) && parseFloat(amt) > 0;
    };

    const signTransaction = (txid, txout, txHex, to_address, amount_in_satoshis, privateKey) => {

        const psbt = new bitcoin.Psbt({network:TESTNET});
        psbt.addInput({
            hash: txid, // reverse order of txid
            index: txout,  // the output index
            nonWitnessUtxo: Buffer.from(txHex, 'hex'),
        });
        psbt.addOutput({
            address: to_address,
            value: amount_in_satoshis,
        });

        const keyPair = ECPair.fromWIF(privateKey, TESTNET);
        psbt.signInput(0, keyPair);
        psbt.finalizeAllInputs();
        const finalTransaction = psbt.extractTransaction();

        return finalTransaction.toHex();
    }

    const broadcastTransaction = (signedTx) => {

        fetch('/broadcast_bitcoin/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Include CSRF token if needed
            },
            body: JSON.stringify({
                signed_tx: signedTx
            })
        })
        .then(response => response.json())
        .then(data => {

            if (data.status === 'success') {
                console.log("Transaction broadcasted successfully:", data.tx_details);
                getConfirmations(data.tx_details)
            } else {
                alert("Could not broadcast transaction (was it correctly signed?)")
                console.error("Error broadcasting transaction:", data.message);
            }
        })
        .catch(error => {

            alert("Could not broadcast transaction (was it correctly signed?)")
            console.error("Error:", error);
        });
    }
    const getConfirmations = (txHash) => {
        setLoading(true);

        fetch('/get_confirmations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Include CSRF token if needed
            },
            body: JSON.stringify({
                hash: txHash
            })
        })
        .then(response => response.json())
        .then(data => {
            setLoading(false);

            if (data.status === 'success') {
                if (data.confirmations < 1)
                {
                    getConfirmations(txHash);
                }
                else
                {
                    alert("Transaction confirmed!");
                    console.log("Transaction confirmed");
                }
            } else {
                alert("Could not confirm transaction")
                console.error("Error broadcasting transaction:", data.message);
            }
        })
        .catch(error => {
            setLoading(false);

            alert("Could not confirm transaction")
            console.error("Error:", error);
        });
    }


    const getCookie = (name) => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const initiateTransaction = () => {
        const privateKeyInput = document.getElementById('privateKeyInput');
        const privateKeyValue = privateKeyInput.value;
        const amount = document.getElementById('amountInput').value;

        if (!isValidAddress(toAddress) || !isValidAddress(fromAddress)) {
            alert("Invalid address provided");
            return;
        }
        if (!isValidPrivateKey(privateKeyValue)) {
            alert("Invalid private key");
            return;
        }
        if (!isValidAmount(amount)) {
            alert("Invalid amount");
            return;
        }

        fetch('/send_bitcoin/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Include CSRF token if needed
            },
            body: JSON.stringify({
                to_address: toAddress,
                from_address: fromAddress,
                amount: amount
            })
        })
        .then(response => response.json())
        .then(data => {
            const signedTx = signTransaction(data.message[0],data.message[1],data.message[2],data.message[3],data.message[4], privateKeyValue);
            // After signing, call the broadcast_signed_transaction endpoint
            broadcastTransaction(signedTx);
        })
        .catch(error => {
            alert("Could not send (did you use the correct private key?)")
            console.error("Error:", error);
        });

        privateKeyInput.value = ''; // clear private key field for security
    }

    return (
        <div>
            <div className="input-group">
                <AddressDropdown
                    placeholder="To Address"
                    fetchEndpoint="/path/to/get_addresses_endpoint/"
                    createEndpoint="/path/to/create_address_endpoint/"
                    onAddressChange={setToAddress}

                />
                <AddressDropdown
                    placeholder="From Address"
                    fetchEndpoint="/path/to/get_addresses_endpoint/"
                    createEndpoint="/path/to/create_address_endpoint/"
                    onAddressChange={setFromAddress}
                />
                <input
                    type="password"
                    placeholder="Private Key"
                    id="privateKeyInput"
                />
                <input id="amountInput" type="text" placeholder="Amount" />
            </div>
            <div className='transaction-container'>
                        <button onClick={initiateTransaction}>Submit</button>
            {loading && <div>Waiting for confirmations...</div>}

            </div>
        </div>
    );
}

export default BitcoinTransaction;
