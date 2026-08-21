package com.jmall.service;

import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * Small, idempotent migrations for databases created by an older Jmall image.
 * Fresh installations still receive the same schema from docker/mysql/init.
 */
@Service
public class SchemaMigrationService {

    private static final Logger log = LoggerFactory.getLogger(SchemaMigrationService.class);
    private final JdbcTemplate jdbcTemplate;

    public SchemaMigrationService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void migrate() {
        Integer subtitleColumns = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.COLUMNS " +
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'jmall_product' " +
                        "AND COLUMN_NAME = 'subtitle'",
                Integer.class
        );

        if (subtitleColumns == null || subtitleColumns == 0) {
            jdbcTemplate.execute(
                    "ALTER TABLE jmall_product ADD COLUMN subtitle VARCHAR(160) " +
                            "NOT NULL DEFAULT '' AFTER title"
            );
            log.info("Added jmall_product.subtitle");
        }

        int backfilled = jdbcTemplate.update(
                "UPDATE jmall_product SET subtitle = LEFT(TRIM(description), 160) " +
                        "WHERE (subtitle IS NULL OR subtitle = '') " +
                        "AND description IS NOT NULL AND TRIM(description) <> ''"
        );
        if (backfilled > 0) {
            log.info("Backfilled subtitles for {} existing products", backfilled);
        }
    }
}
