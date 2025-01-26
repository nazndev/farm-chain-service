INSERT INTO contracts (id, contract_id, buyer_id, seller_id, product_id, agreed_price, delivery_date, status)
VALUES
    (1, 'contract_001', 3, 4, 1, 5000.0, '2025-02-01', 'Pending');

INSERT INTO traceability_records (id, traceability_hash, product_id, farmer_id, aggregation_center_id, `timestamp`)
VALUES
    (1, 'trace_hash_1', 1, 1, 1, UNIX_TIMESTAMP());
