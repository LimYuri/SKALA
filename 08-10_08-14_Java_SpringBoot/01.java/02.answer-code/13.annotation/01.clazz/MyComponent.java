import java.lang.annotation.*;

/**
 * 커스텀 Annotation 정의
 * - @Target: 클래스에만 적용 가능
 * - @Retention: 런타임까지 유지
 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MyComponent {
    String value() default "";  // 이름 설정
}
