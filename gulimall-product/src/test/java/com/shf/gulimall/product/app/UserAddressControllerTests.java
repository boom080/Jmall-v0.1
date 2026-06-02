package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.UserAddressResponse;
import com.shf.gulimall.product.app.service.UserAddressApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class UserAddressControllerTests {

    private MockMvc mockMvc;
    private UserAddressApplicationService userAddressApplicationService;

    @Before
    public void setUp() {
        userAddressApplicationService = mock(UserAddressApplicationService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(new UserAddressController(userAddressApplicationService)).build();
    }

    @Test
    public void listReturnsAddressArray() throws Exception {
        UserAddressResponse address = new UserAddressResponse();
        address.setId(5L);
        address.setName("Alice");
        address.setPhone("13800000000");
        address.setDetailAddress("Road 1");
        address.setDefaultStatus(1);

        when(userAddressApplicationService.listCurrentUserAddresses()).thenReturn(Collections.singletonList(address));

        mockMvc.perform(get("/user/addresses"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].name").value("Alice"));
    }

    @Test
    public void createReturnsSavedAddress() throws Exception {
        UserAddressResponse address = new UserAddressResponse();
        address.setId(5L);
        address.setName("Alice");
        address.setPhone("13800000000");
        address.setDetailAddress("Road 1");

        when(userAddressApplicationService.createAddress(any())).thenReturn(address);

        mockMvc.perform(post("/user/addresses")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Alice\",\"phone\":\"13800000000\",\"detailAddress\":\"Road 1\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value(5));
    }

    @Test
    public void updateReturnsUpdatedAddress() throws Exception {
        UserAddressResponse address = new UserAddressResponse();
        address.setId(5L);
        address.setName("Bob");

        when(userAddressApplicationService.updateAddress(eq(5L), any())).thenReturn(address);

        mockMvc.perform(put("/user/addresses/5")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Bob\",\"phone\":\"13800000001\",\"detailAddress\":\"Road 2\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.name").value("Bob"));
    }

    @Test
    public void deleteReturnsOk() throws Exception {
        mockMvc.perform(delete("/user/addresses/5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }
}





