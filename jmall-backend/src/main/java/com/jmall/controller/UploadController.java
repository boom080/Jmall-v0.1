package com.jmall.controller;

import com.jmall.common.R;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/upload")
public class UploadController {

    @Value("${jmall.upload.dir:-}")
    private String uploadDir;

    private Path getUploadDir() {
        if (uploadDir == null || uploadDir.isBlank()) {
            return Paths.get("uploads").toAbsolutePath().normalize();
        }
        return Paths.get(uploadDir).toAbsolutePath().normalize();
    }

    @PostMapping("/image")
    public R uploadImage(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return R.error(400, "file is empty");
        }

        // Validate file type
        String contentType = file.getContentType();
        if (contentType == null || !contentType.startsWith("image/")) {
            return R.error(400, "only image files are allowed");
        }

        // Validate size (max 5MB)
        if (file.getSize() > 5 * 1024 * 1024) {
            return R.error(400, "file size exceeds 5MB limit");
        }

        try {
            // Organize by date: uploads/YYYY-MM-DD/uuid.ext
            String dateDir = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
            Path baseDir = getUploadDir().resolve(dateDir);
            Files.createDirectories(baseDir);

            String originalName = file.getOriginalFilename();
            String ext = "";
            if (originalName != null && originalName.contains(".")) {
                ext = originalName.substring(originalName.lastIndexOf('.'));
            }
            String filename = UUID.randomUUID().toString().substring(0, 8) + ext;
            Path targetPath = baseDir.resolve(filename);

            try (var input = file.getInputStream()) {
                Files.copy(input, targetPath, StandardCopyOption.REPLACE_EXISTING);
            }

            // Return the relative URL path
            String url = "/uploads/" + dateDir + "/" + filename;
            return R.ok(url);

        } catch (IOException e) {
            return R.error(50001, "图片上传失败，请稍后重试");
        }
    }

    @PostMapping("/images")
    public R uploadImages(@RequestParam("files") List<MultipartFile> files) {
        if (files == null || files.isEmpty()) {
            return R.error(400, "no files provided");
        }

        List<String> urls = new ArrayList<>();
        for (MultipartFile file : files) {
            R result = uploadImage(file);
            if (result.getCode() == 10000) {
                urls.add((String) result.getData());
            }
        }

        return R.ok(urls);
    }
}
