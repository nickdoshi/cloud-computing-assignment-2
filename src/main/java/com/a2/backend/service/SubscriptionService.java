package com.a2.backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class SubscriptionService {

    private final DynamoDbClient dynamoDb;
    private final MusicService musicService;

    @Value("${aws.dynamodb.table.subscriptions:subscriptions}")
    private String subscriptionsTable;

    public SubscriptionService(DynamoDbClient dynamoDb, MusicService musicService) {
        this.dynamoDb = dynamoDb;
        this.musicService = musicService;
    }

    public List<Map<String, String>> getSubscriptions(String email) {
        QueryResponse response = dynamoDb.query(QueryRequest.builder()
                .tableName(subscriptionsTable)
                .keyConditionExpression("email = :email")
                .expressionAttributeValues(Map.of(":email", AttributeValue.fromS(email)))
                .build());

        return response.items().stream()
                .map(this::toSubscriptionMap)
                .collect(Collectors.toList());
    }

    // subscription_id = "artist#title" — natural key that prevents duplicate subscriptions.
    public void addSubscription(String email, String title, String artist, String year, String album) {
        String subscriptionId = artist + "#" + title;
        String imageKey = musicService.getImageKey(artist, title);

        Map<String, AttributeValue> item = new HashMap<>();
        item.put("email", AttributeValue.fromS(email));
        item.put("subscription_id", AttributeValue.fromS(subscriptionId));
        item.put("title", AttributeValue.fromS(title));
        item.put("artist", AttributeValue.fromS(artist));
        item.put("year", AttributeValue.fromS(year));
        item.put("album", AttributeValue.fromS(album));
        item.put("image_url", AttributeValue.fromS(imageKey));

        dynamoDb.putItem(PutItemRequest.builder()
                .tableName(subscriptionsTable)
                .item(item)
                .build());
    }

    public void removeSubscription(String email, String subscriptionId) {
        dynamoDb.deleteItem(DeleteItemRequest.builder()
                .tableName(subscriptionsTable)
                .key(Map.of(
                        "email", AttributeValue.fromS(email),
                        "subscription_id", AttributeValue.fromS(subscriptionId)
                ))
                .build());
    }

    private Map<String, String> toSubscriptionMap(Map<String, AttributeValue> item) {
        Map<String, String> sub = new HashMap<>();
        sub.put("subscription_id", getString(item, "subscription_id"));
        sub.put("title", getString(item, "title"));
        sub.put("artist", getString(item, "artist"));
        sub.put("year", getString(item, "year"));
        sub.put("album", getString(item, "album"));
        sub.put("image_url", musicService.generatePresignedUrl(getString(item, "image_url")));
        return sub;
    }

    private String getString(Map<String, AttributeValue> item, String key) {
        AttributeValue val = item.get(key);
        return (val != null && val.s() != null) ? val.s() : "";
    }
}
