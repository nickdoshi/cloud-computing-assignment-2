package com.a2.backend.controller;

import com.a2.backend.service.MusicService;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;
import java.util.List;
import java.util.Map;
// template for music query, you can modify it as you like
@RestController
public class MusicController {

    private final MusicService musicService;

    public MusicController(MusicService musicService) {
        this.musicService = musicService;
    }

    /**
     * GET /music
     *
     * Accepts up to four optional query parameters: title, year, artist, album.
     * At least one must be non-empty (enforced on the frontend).
     * Multiple parameters are combined with AND logic.
     *
     * Examples:
     *   GET /music?artist=Taylor+Swift&album=Fearless
     *   GET /music?year=1974&artist=Jimmy+Buffett
     *
     * Returns a JSON array of matching songs, each with fields:
     *   title, artist, year, album, image_url (pre-signed S3 URL)
     * Returns an empty array [] if nothing matches — the frontend shows
     * "No result is retrieved. Please query again" in that case.
     *
     * TODO: call musicService.query(title, year, artist, album) and return the result.
     */
    @GetMapping("/music")
    public List<Map<String, String>> queryMusic(
            @RequestParam(required = false) String title,
            @RequestParam(required = false) String year,
            @RequestParam(required = false) String artist,
            @RequestParam(required = false) String album) {
        // TODO: implement — replace with: return musicService.query(title, year, artist, album);
        return Collections.emptyList();
    }
}
