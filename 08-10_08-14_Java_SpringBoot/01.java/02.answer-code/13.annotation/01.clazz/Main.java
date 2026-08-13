/**
 * Reflection을 이용하여 Annotation 정보 읽기
 * 
 * 동작:
 * 1. OrderService 클래스의 @MyComponent annotation 확인
 * 2. annotation에서 value() 값 추출
 * 3. 콘솔에 출력
 */
public class Main {
    public static void main(String[] args) {
        // 1단계: OrderService 클래스 객체 가져오기
        Class<?> clazz = OrderService.class;
        
        // 2단계: @MyComponent Annotation이 OrderService 클래스 객체에 있는지 확인
        if (clazz.isAnnotationPresent(MyComponent.class)) {
            // 3단계: Annotation 객체 가져오기
            MyComponent annotation = clazz.getAnnotation(MyComponent.class);
            
            // 4단계: Annotation의 value() 메서드 호출
            String componentName = annotation.value();
            
            // 5단계: 결과 출력
            System.out.println("Annotation Name: " + componentName);
            System.out.println("Class Name: " + clazz.getName());
        } else {
            System.out.println("@MyComponent annotation이 없습니다");
        }
    }
}
