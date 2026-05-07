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

    /**
     * Main query method called by the controller.
     * - If artist is provided: use DynamoDB Query on the base table (artist is the partition key).
     * - If artist is NOT provided: use DynamoDB Scan with a FilterExpression.
     * - All non-empty fields are combined with AND logic.
     * - Returns a list of song maps with a pre-signed S3 URL for the artist image.
     *
     * TODO: implement query logic using buildFilterParts(), then map results via toSongMap().
     */
    public List<Map<String, String>> query(String title, String year, String artist, String album) {
        Map<String, String> names = new HashMap<>();
        Map<String, AttributeValue> values = new HashMap<>();

        List<String> filterParts = buildFilterParts(title, year, album, names, values);

        // Scan with a filter expression
        if (artist == null || artist.isBlank()) {
            ScanRequest.Builder scanBuilder = ScanRequest.builder().tableName(musicTable);

            if (!filterParts.isEmpty()) {
                scanBuilder.filterExpression(String.join(" AND ", filterParts)).expressionAttributeNames(names).expressionAttributeValues(values);
            }
            ScanResponse scanResponse = dynamoDb.scan(scanBuilder.build());
            return scanResponse.items().stream().map(this::toSongMap).collect(Collectors.toList());
        }

        names.put("#artist", "artist");
        values.put(":artist", AttributeValue.fromS(artist));

        // Query with partition key
        QueryRequest.Builder queryBuilder =
                QueryRequest.builder().tableName(musicTable).keyConditionExpression("#artist = :artist").expressionAttributeNames(names).expressionAttributeValues(values);
        // Apply filter expression on other fields
        if (!filterParts.isEmpty()) {
            queryBuilder.filterExpression(String.join(" AND ", filterParts));
        }
        QueryResponse response = dynamoDb.query(queryBuilder.build());
        return response.items().stream().map(this::toSongMap).collect(Collectors.toList());

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

        try{
            GetObjectRequest getObjectRequest =
                    GetObjectRequest.builder().bucket(bucketName).key(s3Key).build();

            GetObjectPresignRequest presignRequest =
                    GetObjectPresignRequest.builder().signatureDuration(Duration.ofHours(1)).getObjectRequest(getObjectRequest).build();
        }
        catch (Exception e){
            return "";
        }

        return "";
    }

    /**
     * Builds the DynamoDB FilterExpression parts for title, year, and album.
     * Populates the provided names and values maps with expression attribute aliases.
     *
     * - title  → contains(#title, :title)   (partial match)
     * - year   → #yr = :year                (exact match — "year" is a DynamoDB reserved word)
     * - album  → contains(#album, :album)   (partial match)
     *
     */
    private List<String> buildFilterParts(String title, String year, String album,
                                          Map<String, String> names,
                                          Map<String, AttributeValue> values) {
        List<String> parts = new ArrayList<>();
        if (title != null && !title.isBlank()) {
            names.put("#title", "title");
            values.put(":title", AttributeValue.fromS(title));
            parts.add("contains(#title, :title)");
        }

        if (year != null && !year.isBlank()) {
            names.put("#yr", "year");
            values.put(":year", AttributeValue.fromS(year));
            parts.add("#yr = :year");
        }

        if (album != null && !album.isBlank()) {
            names.put("#album", "album");
            values.put(":album", AttributeValue.fromS(album));
            parts.add("contains(#album, :album)");
        }

        return parts;
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
