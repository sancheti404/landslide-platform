package com.landslide.backend.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI landslideOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Landslide Risk Management API")
                        .description("Backend REST API for spatial landslide event tracking, risk zone management, infrastructure proximity query, and GIS spatial intelligence.")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Landslide Platform Team")));
    }
}
