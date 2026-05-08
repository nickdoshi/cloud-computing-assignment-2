package com.a2.backend.controller;

import com.a2.backend.model.SubscribeRequest;
import com.a2.backend.service.SubscriptionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/subscriptions")
public class SubscriptionController {

    private final SubscriptionService subscriptionService;

    public SubscriptionController(SubscriptionService subscriptionService) {
        this.subscriptionService = subscriptionService;
    }

    @GetMapping("/{email}")
    public List<Map<String, String>> getSubscriptions(@PathVariable String email) {
        return subscriptionService.getSubscriptions(email);
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> subscribe(@RequestBody SubscribeRequest req) {
        subscriptionService.addSubscription(
                req.email(), req.title(), req.artist(), req.year(), req.album(), req.imageUrl());
        return ResponseEntity.status(201).body(Map.of("success", true));
    }

    // subscriptionId is URL-encoded "artist#title#year#album".
    @DeleteMapping("/{email}/{subscriptionId}")
    public ResponseEntity<Map<String, Object>> unsubscribe(
            @PathVariable String email,
            @PathVariable String subscriptionId) {
        subscriptionService.removeSubscription(email, subscriptionId);
        return ResponseEntity.ok(Map.of("success", true));
    }
}
