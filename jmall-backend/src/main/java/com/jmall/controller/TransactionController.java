package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.dto.PurchaseRequest;
import com.jmall.service.TransactionService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/transactions")
public class TransactionController {

    private final TransactionService transactionService;

    public TransactionController(TransactionService transactionService) {
        this.transactionService = transactionService;
    }

    @PostMapping
    public R purchase(@Valid @RequestBody PurchaseRequest request) {
        return transactionService.purchase(request.getProductId());
    }
}
