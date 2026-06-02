package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.app.dto.UserAuthLoginResponse;
import com.shf.gulimall.product.app.service.UserAuthApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class UserAuthControllerTests {

    private MockMvc mockMvc;
    private UserAuthApplicationService userAuthApplicationService;

    @Before
    public void setUp() {
        userAuthApplicationService = mock(UserAuthApplicationService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(new UserAuthController(userAuthApplicationService)).build();
    }

    @Test
    public void registerReturnsOk() throws Exception {
        mockMvc.perform(post("/user/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userName\":\"alice\",\"phone\":\"13800000000\",\"password\":\"123456\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    public void loginReturnsTokenAndUser() throws Exception {
        UserAuthLoginResponse response = new UserAuthLoginResponse();
        response.setToken("token-1");
        CurrentUserProfile profile = new CurrentUserProfile();
        profile.setUserId(101L);
        profile.setUsername("alice");
        profile.setDisplayName("Alice");
        response.setUser(profile);

        when(userAuthApplicationService.login(any())).thenReturn(response);

        mockMvc.perform(post("/user/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"loginacct\":\"alice\",\"password\":\"123456\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.token").value("token-1"))
                .andExpect(jsonPath("$.data.user.displayName").value("Alice"));
    }

    @Test
    public void meReturnsUnauthorizedWhenMissingLogin() throws Exception {
        when(userAuthApplicationService.me()).thenThrow(new IllegalStateException("请先登录"));

        mockMvc.perform(get("/user/auth/me"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(401));
    }

    @Test
    public void logoutReturnsOk() throws Exception {
        mockMvc.perform(post("/user/auth/logout"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }
}





