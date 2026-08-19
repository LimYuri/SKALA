package com.skala.ch02.domain;

public class Order {
    private final String id;
    private final String ownerId;
    private final String item;
    private final String status;
    private final String eta;

    public Order(String id, String ownerId, String item, String status, String eta) {
        this.id = id;
        this.ownerId = ownerId;
        this.item = item;
        this.status = status;
        this.eta = eta;
    }

    public String getId() { return id; }
    public String getOwnerId() { return ownerId; }
    public String getItem() { return item; }
    public String getStatus() { return status; }
    public String getEta() { return eta; }
}
