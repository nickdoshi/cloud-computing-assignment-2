package com.a2.backend.model;

public record SubscribeRequest(
        String email,
        String title,
        String artist,
        String year,
        String album
) {}
