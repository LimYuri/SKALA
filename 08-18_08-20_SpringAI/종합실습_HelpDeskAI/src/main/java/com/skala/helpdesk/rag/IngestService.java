package com.skala.helpdesk.rag;

import com.skala.helpdesk.config.HelpDeskProperties;
import java.io.IOException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.ai.document.Document;
import org.springframework.ai.reader.tika.TikaDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

// 반품/배송 규정 문서를 청크로 쪼개서 VectorStore에 넣는 역할.
// 문서 목록은 지금은 2개뿐이라 그냥 하드코딩했음 - 늘어나면 설정 파일로 빼는 게 나을 듯
@Service
public class IngestService {
    private final VectorStore vectorStore;
    private final HelpDeskProperties props;
    private final List<DocSpec> documents = List.of(
            new DocSpec("helpdesk-docs/return-policy.md", "반품·교환 규정", "POLICY", "CS"),
            new DocSpec("helpdesk-docs/shipping-policy.md", "배송 규정", "POLICY", "LOGISTICS"));
    public IngestService(VectorStore vectorStore, HelpDeskProperties props) {
        this.vectorStore = vectorStore; this.props = props;
    }
    public List<IngestResult> ingestAll() {
        List<IngestResult> results = new ArrayList<>();
        for (DocSpec spec : documents) results.add(ingest(spec));
        return results;
    }
    // 재인제스트할 때 중복 안 쌓이게 같은 source는 지우고 다시 넣는 방식.
    // version은 인제스트한 날짜로 찍어서 언제 최신화됐는지 바로 확인 가능하게 함
    private IngestResult ingest(DocSpec spec) {
        var resource = new ClassPathResource(spec.path());
        String source = resource.getFilename();
        vectorStore.delete(new FilterExpressionBuilder().eq("source", source).build());
        List<Document> raw = new TikaDocumentReader(resource).get();
        List<Document> chunks = TokenTextSplitter.builder().withChunkSize(props.rag().chunkSize())
                .withMinChunkSizeChars(props.rag().minChunkSizeChars()).build().apply(raw);
        String version = LocalDate.now().toString();
        List<Document> enriched = chunks.stream().map(chunk -> {
            Map<String, Object> metadata = new HashMap<>(chunk.getMetadata());
            metadata.put("source", source); metadata.put("title", spec.title());
            metadata.put("docType", spec.docType()); metadata.put("dept", spec.dept());
            metadata.put("version", version);
            return new Document(chunk.getText(), metadata);
        }).toList();
        vectorStore.add(enriched);
        return new IngestResult(source, enriched.size(), version);
    }
    public List<ChunkView> inspect(String q, int topK) {
        return vectorStore.similaritySearch(SearchRequest.builder().query(q).topK(topK).build()).stream()
                .map(d -> new ChunkView(String.valueOf(d.getMetadata().get("source")),
                        String.valueOf(d.getMetadata().get("version")), d.getScore(),
                        d.getText().substring(0, Math.min(160, d.getText().length())))).toList();
    }
    private record DocSpec(String path, String title, String docType, String dept) {}
    public record IngestResult(String source, int chunks, String version) {}
    public record ChunkView(String source, String version, Double score, String preview) {}
}
