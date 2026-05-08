package com.a2.backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;

import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;
// template for music query, you can modify it as you like
@Service
public class MusicService {

    private final DynamoDbClient dynamoDb;
    private final S3Presigner s3Presigner;

    @Value("${aws.dynamodb.table.music:music}")
    private String musicTable;

    @Value("${aws.s3.bucket-name}")
    private String bucketName;

    public MusicService(DynamoDbClient dynamoDb, S3Presigner s3Presigner) {
        this.dynamoDb = dynamoDb;
        this.s3Presigner = s3Presigner;
    }

    public List<Map<String, String>> query(String title, String year, String artist, String album) {
        List<Map<String, AttributeValue>> items = new ArrayList<>();
        ScanRequest.Builder scanBuilder = ScanRequest.builder().tableName(musicTable);
        ScanResponse response;

        do {
            response = dynamoDb.scan(scanBuilder.build());
            items.addAll(response.items());
            scanBuilder.exclusiveStartKey(response.lastEvaluatedKey());
        } while (response.hasLastEvaluatedKey() && !response.lastEvaluatedKey().isEmpty());

        return items.stream()
                .filter(item -> matchesQuery(item, title, year, artist, album))
                .map(this::toSongMap)
                .collect(Collectors.toList());
    }

    /**
     * Looks up a single music record by its primary key (artist + title_year_album) and returns
     * the raw S3 object key stored in the "image_url" attribute.
     * Used by SubscriptionService when saving a new subscription.
     *
     */
    public String getImageKey(String artist, String title, String year, String album) {
        Map<String, AttributeValue> key = new HashMap<>();
        key.put("artist", AttributeValue.fromS(artist));

        String title_year_album = title + "#" + year + "#" + album;
        key.put("title_year_album", AttributeValue.fromS(title_year_album));

        GetItemRequest itemRequest =
                GetItemRequest.builder().tableName(musicTable).key(key).build();

        GetItemResponse response = dynamoDb.getItem(itemRequest);

        if (response.item() != null) {
            return  getString(response.item(), "image_url");
        }

        return "";
    }

    /**
     * Takes an S3 object key (e.g. "artist-images/taylor-swift.jpg") and returns
     * a temporary pre-signed GET URL valid for 1 hour so the frontend can display the image.
     * Return an empty string if the key is blank or if presigning fails.
     *
     */
    public String generatePresignedUrl(String s3Key) {
        if (s3Key == null || s3Key.isBlank()) return "";
        if (s3Key.startsWith("http://") || s3Key.startsWith("https://")) return s3Key;

        try{
            GetObjectRequest getObjectRequest =
                    GetObjectRequest.builder().bucket(bucketName).key(s3Key).build();

            GetObjectPresignRequest presignRequest =
                    GetObjectPresignRequest.builder().signatureDuration(Duration.ofHours(1)).getObjectRequest(getObjectRequest).build();
            return s3Presigner.presignGetObject(presignRequest).url().toString();
        }
        catch (Exception e){
            return "";
        }
    }

    private boolean matchesQuery(Map<String, AttributeValue> item, String title, String year, String artist, String album) {
        return containsIgnoreCase(getString(item, "title"), title)
                && containsIgnoreCase(getString(item, "year"), year)
                && containsIgnoreCase(getString(item, "artist"), artist)
                && containsIgnoreCase(getString(item, "album"), album);
    }

    private boolean containsIgnoreCase(String value, String query) {
        if (query == null || query.isBlank()) return true;
        return value != null && value.toLowerCase(Locale.ROOT).contains(query.trim().toLowerCase(Locale.ROOT));
    }

    /**
     * Converts a raw DynamoDB item map into a plain String map for the API response.
     * Fields: title, artist, year, album, image_url (pre-signed URL via generatePresignedUrl()).
     *.
     */
    private Map<String, String> toSongMap(Map<String, AttributeValue> item) {        Map<String, String> song = new HashMap<>();
        song.put("title",     getString(item, "title"));
        song.put("artist",    getString(item, "artist"));
        song.put("year",      getString(item, "year"));
        song.put("album",     getString(item, "album"));
        song.put("image_url", generatePresignedUrl(getString(item, "image_url")));
        return song;
    }

    /**
     * Helper: safely extracts the String value of a DynamoDB attribute.
     * Returns an empty string if the attribute is missing or null.
     */
    private String getString(Map<String, AttributeValue> item, String key) {
        AttributeValue val = item.get(key);
        return (val != null && val.s() != null) ? val.s() : "";
    }
}
