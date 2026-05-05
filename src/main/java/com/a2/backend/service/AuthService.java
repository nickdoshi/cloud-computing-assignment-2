package com.a2.backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Service
public class AuthService {

    private final DynamoDbClient dynamoDb;

    @Value("${aws.dynamodb.table.login:login}")
    private String loginTable;

    public AuthService(DynamoDbClient dynamoDb) {
        this.dynamoDb = dynamoDb;
    }

    public Optional<String> login(String email, String password) {
        GetItemResponse response = dynamoDb.getItem(GetItemRequest.builder()
                .tableName(loginTable)
                .key(Map.of("email", AttributeValue.fromS(email)))
                .build());

        if (!response.hasItem()) return Optional.empty();

        Map<String, AttributeValue> item = response.item();
        String stored = item.getOrDefault("password", AttributeValue.fromS("")).s();
        if (!stored.equals(password)) return Optional.empty();

        return Optional.of(item.getOrDefault("user_name", AttributeValue.fromS("")).s());
    }

    // Returns false if email already exists, true on success.
    public boolean register(String email, String userName, String password) {
        GetItemResponse existing = dynamoDb.getItem(GetItemRequest.builder()
                .tableName(loginTable)
                .key(Map.of("email", AttributeValue.fromS(email)))
                .build());
        if (existing.hasItem()) return false;

        Map<String, AttributeValue> item = new HashMap<>();
        item.put("email", AttributeValue.fromS(email));
        item.put("user_name", AttributeValue.fromS(userName));
        item.put("password", AttributeValue.fromS(password));

        dynamoDb.putItem(PutItemRequest.builder()
                .tableName(loginTable)
                .item(item)
                .build());
        return true;
    }
}
