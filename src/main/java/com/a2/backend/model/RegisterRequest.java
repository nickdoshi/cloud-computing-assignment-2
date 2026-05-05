package com.a2.backend.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RegisterRequest(
        String email,
        @JsonProperty("user_name") String userName,
        String password
) {}
