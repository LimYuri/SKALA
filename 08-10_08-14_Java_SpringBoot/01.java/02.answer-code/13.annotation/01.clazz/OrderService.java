/**
 * @MyComponent Annotation이 적용된 서비스 클래스
 */
@MyComponent("orderService")
public class OrderService {
    public void processOrder() {
        System.out.println("주문 처리 중...");
    }
}
