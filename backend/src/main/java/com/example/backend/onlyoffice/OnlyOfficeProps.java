package com.example.backend.onlyoffice;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "onlyoffice")
public class OnlyOfficeProps {
    private String jwtSecret;
    private String callbackUrl;
    private String publicBase;

    public String getJwtSecret() { return jwtSecret; }
    public void setJwtSecret(String v) { this.jwtSecret = v; }
    public String getCallbackUrl() { return callbackUrl; }
    public void setCallbackUrl(String v) { this.callbackUrl = v; }
    public String getPublicBase() { return publicBase; }
    public void setPublicBase(String v) { this.publicBase = v; }
}
