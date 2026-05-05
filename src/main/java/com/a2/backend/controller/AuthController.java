package com.a2.backend.controller;

import com.a2.backend.model.LoginRequest;
import com.a2.backend.model.RegisterRequest;
import com.a2.backend.service.AuthService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody LoginRequest req) {
        Optional<String> userName = authService.login(req.email(), req.password());
        if (userName.isPresent()) {
            return ResponseEntity.ok(Map.of("success", true, "user_name", userName.get()));
        }
        return ResponseEntity.status(401)
                .body(Map.of("success", false, "message", "email or password is invalid"));
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody RegisterRequest req) {
        boolean created = authService.register(req.email(), req.userName(), req.password());
        if (created) {
            return ResponseEntity.status(201).body(Map.of("success", true));
        }
        return ResponseEntity.status(409)
                .body(Map.of("success", false, "message", "The email already exists"));
    }
}
