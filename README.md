# Digital Wallet Backend

A secure wallet system built with Python + Flask, supporting multi-currency accounts, transaction logging, fraud detection, and admin review.

## Features

- JWT-based authentication
- Deposit, Withdraw, Transfer
- Fraud detection (flag large withdrawals & frequent transfers)
- Admin dashboard APIs
- Mock email alerts

## Postman API Collection

🧪 [Download API Collection](postman/digital_wallet_api.postman_collection.json)

This Postman collection includes all routes:
- Register, Login
- Deposit, Withdraw, Transfer
- Transaction History
- Admin routes (flag review, top users, total balances)