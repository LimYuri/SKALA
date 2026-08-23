package com.example.day2.lab2;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.ClassPathResource;

class Lab2IngestServiceTest {
    @SuppressWarnings("unchecked")
    @Test
    void 재인제스트할_때_삭제조건과_청크_source가_같다() {
        VectorStore store = mock(VectorStore.class);
        Lab2Properties properties = new Lab2Properties(400, 1, 1, 100, true, 0,
                4, 0.5, "test-v1");
        Lab2IngestService service = new Lab2IngestService(store, properties);

        service.ingest(new ClassPathResource("lab2-docs/membership.md"),
                "membership.md", "test-v1");
        service.ingest(new ClassPathResource("lab2-docs/membership.md"),
                "membership.md", "test-v1");

        ArgumentCaptor<List<Document>> chunksCaptor = ArgumentCaptor.forClass(List.class);
        verify(store, times(2)).delete(any(org.springframework.ai.vectorstore.filter.Filter.Expression.class));
        verify(store, times(2)).add(chunksCaptor.capture());
        assertThat(chunksCaptor.getAllValues()).allSatisfy(chunks ->
                assertThat(chunks).allSatisfy(chunk -> {
                    assertThat(chunk.getMetadata().get("source")).isEqualTo("membership.md");
                    assertThat(chunk.getMetadata().get("version")).isEqualTo("test-v1");
                }));
    }
}
