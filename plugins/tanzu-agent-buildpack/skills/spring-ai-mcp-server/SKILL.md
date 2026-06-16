---
name: spring-ai-mcp-server
description: Scaffold a new MCP (Model Context Protocol) server using Spring AI 2.0 / Spring Boot 4 and the Streamable-HTTP transport. Use this skill whenever the user asks to create, scaffold, add, or build a new MCP server or expose a set of tools (math, weather, lookup, CRUD, etc.) via MCP using Java/Spring. Produces a self-contained Maven project in its own subdirectory with @McpTool-annotated tool methods, ready to build, run locally, and (optionally) deploy via the tanzu-agent-deploy skill.
---

# Authoring a Spring AI MCP Server

This skill captures the proven recipe for building a Java MCP server with
Spring AI 2.0: a Maven project in its own subdirectory, the Streamable-HTTP
WebMVC server starter, and tools exposed via the `@McpTool` annotation
(auto-discovered — no manual `ToolCallbackProvider` bean needed).

Reference docs if more depth is needed:
- https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html
- https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-overview.html
- https://docs.spring.io/spring-ai/reference/api/mcp/mcp-streamable-http-server-boot-starter-docs.html

## 1. Project layout

Create a new Maven project in its own subdirectory at the repo root, named
for what it does (e.g. `mcp-server`, `weather-mcp-server`). Organize Java
code **package-by-feature** — one package per group of related tools, not
per architectural layer:

```
<name>-mcp-server/
├── pom.xml
├── .gitignore
└── src/main/
    ├── java/com/example/<name>mcpserver/
    │   ├── <Name>McpServerApplication.java
    │   └── <feature>/
    │       └── <Feature>Tools.java
    └── resources/
        └── application.yml
```

## 2. pom.xml

Spring Boot 4.0.x parent + Spring AI 2.0 BOM + the Streamable-HTTP WebMVC
server starter:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>4.0.0</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>name-mcp-server</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>name-mcp-server</name>

    <properties>
        <java.version>21</java.version>
        <spring-ai.version>2.0.0</spring-ai.version>
    </properties>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.ai</groupId>
                <artifactId>spring-ai-bom</artifactId>
                <version>${spring-ai.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

Use `spring-ai-starter-mcp-server-webflux` instead only if the tools are
reactive/non-blocking; the config below is identical either way.

## 3. application.yml

```yaml
spring:
  application:
    name: <name>-mcp-server
  ai:
    mcp:
      server:
        protocol: STREAMABLE
        name: <name>-mcp-server
        version: 0.0.1
        type: SYNC
        streamable-http:
          mcp-endpoint: /mcp
```

## 4. Application class

Keep it minimal — `@McpTool` methods on any Spring bean are discovered
automatically by the annotation scanner that ships enabled-by-default with
the MCP Boot Starter. **Do not** add a `ToolCallbackProvider` bean; it's
unnecessary with `@McpTool` and risks a bean-name collision with the
`@Service`-named tool bean (e.g. a bean method `weatherTools` colliding with
the `@Service class WeatherTools` bean also named `weatherTools`).

```java
package com.example.namemcpserver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class NameMcpServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(NameMcpServerApplication.class, args);
    }
}
```

## 5. Tool classes

Annotate each tool method with `@McpTool` (tool name + description) and each
parameter with `@McpToolParam` (description + required). This generates the
JSON schema automatically — no manual schema authoring.

```java
package com.example.namemcpserver.weather;

import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.ai.mcp.annotation.McpToolParam;
import org.springframework.stereotype.Service;

@Service
public class WeatherTools {

    @McpTool(name = "get_forecast", description = "Get the weather forecast for a city")
    public String getForecast(
            @McpToolParam(description = "City name", required = true) String city) {
        // ...
    }
}
```

Validate inputs and throw `IllegalArgumentException` for invalid arguments —
the MCP server reports this back to the caller as a tool error.

## 6. Build and verify locally

```bash
cd <name>-mcp-server
mvn -q -DskipTests package
mvn spring-boot:run   # or -Dspring-boot.run.arguments=--server.port=8099 if 8080 is taken
```

Confirm tools registered (look for `Registered tools: N` in the startup log),
then exercise the Streamable-HTTP endpoint directly:

```bash
# 1. Initialize a session and capture the Mcp-Session-Id response header
curl -sS -i -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'

# 2. List tools (reuse the Mcp-Session-Id header)
curl -sS -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 3. Call a tool
curl -sS -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"<tool>","arguments":{...}}}'
```

Add a `.gitignore` with `target/`, `*.iml`, `.idea/` for the new module.

## 7. Deploying to Tanzu Platform

Once it builds and the tools work locally, use the `tanzu-agent-deploy`
skill to `cf push` the jar (java buildpack, ~1G memory), bind it to the MCP
Gateway, and wire it into an agent via a `mcp-server`-tagged user-provided
service.
