import './polyfill'; // Ensure this is imported before any other module that might use Buffer
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import BitcoinTransaction from './transactionComponent'; // Import the new component
import Details from './detailsComponent'; // Import the new component
import './App.scss';

function App() {

    return (
        <Router>
            <div className="container">
                <header>Bitcoin Transferrer</header>
                <Routes>
                    <Route path="/" element={<BitcoinTransaction />} />
                    <Route path="/path-to-details/:bookId" element={<Details />} />
                </Routes>
                <footer>Remember to double-check your details before submitting.</footer>
            </div>
        </Router>
    );
}

export default App;
