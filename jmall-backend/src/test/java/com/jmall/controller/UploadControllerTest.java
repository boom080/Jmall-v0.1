package com.jmall.controller;

import com.jmall.common.R;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class UploadControllerTest {

    @TempDir
    Path uploadDir;

    @Test
    void uploadImageStoresFileInConfiguredAbsoluteDirectory() throws Exception {
        UploadController controller = new UploadController();
        ReflectionTestUtils.setField(controller, "uploadDir", uploadDir.toString());
        MockMultipartFile image = new MockMultipartFile(
                "file", "商品图.png", "image/png", new byte[]{1, 2, 3, 4}
        );

        R result = controller.uploadImage(image);

        assertEquals(10000, result.getCode());
        String url = String.valueOf(result.getData());
        assertTrue(url.startsWith("/uploads/"));
        Path relativeFile = Path.of(url.substring("/uploads/".length()));
        assertTrue(Files.exists(uploadDir.resolve(relativeFile)));
        assertEquals(4, Files.size(uploadDir.resolve(relativeFile)));
    }
}
