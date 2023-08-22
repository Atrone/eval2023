import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './Details.scss';

function Details() {
    const { bookId } = useParams();
    const [book, setBook] = useState(null);

    useEffect(() => {
        fetch(`/api/path-to-details/${bookId}/`)
            .then(response => response.json())
            .then(data => setBook(data));
    }, [bookId]);

    if (!book) return <div>Loading...</div>;
    const qrBaseUrl = "https://chart.googleapis.com/chart?chs=225x225&chld=L|2&cht=qr&chl=";
    const qrData = `bitcoin:${book.address}`;
    const qrLink = qrBaseUrl + encodeURIComponent(qrData);
    return (
        <div className="centered-content">
            <img src={qrLink} alt="QR Code for Address" />
            <h1>Address: {book.address}</h1>
            <p>Total Received: {book.total_received}</p>
            <p>Total Sent: {book.total_sent}</p>
            <p>Balance: {book.balance}</p>
            <p>Unconfirmed Balance: {book.unconfirmed_balance}</p>
            <p>Final Balance: {book.final_balance}</p>
            <p>Transactions: {book.n_tx}</p>
            <p>Unconfirmed Transactions: {book.unconfirmed_n_tx}</p>
            <p>Final Transactions: {book.final_n_tx}</p>
        </div>
    );
}

export default Details;
