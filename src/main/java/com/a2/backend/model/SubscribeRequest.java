package com.a2.backend.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record SubscribeRequest(
        String email,
        String title,
        String artist,
        String year,
        String album,
        @JsonProperty("image_url") String imageUrl
) {}
