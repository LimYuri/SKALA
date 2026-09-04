package com.lecture.course.entity;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CourseGearHubTests {

    @Test
    void borrowOneDecreasesStockAndIncreasesUsage() {
        Course course = ownedCourse(2);

        course.borrowOne();

        assertThat(course.getAvailableQuantity()).isEqualTo(1);
        assertThat(course.getEnrollmentCount()).isEqualTo(1);
    }

    @Test
    void cannotBorrowWhenStockIsEmpty() {
        Course course = ownedCourse(0);

        assertThatThrownBy(course::borrowOne)
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("대여 가능한 수량");
    }

    private Course ownedCourse(int availableQuantity) {
        return Course.builder()
                .title("테스트 교보재")
                .category(Course.Category.DEVICE)
                .price(BigDecimal.valueOf(100_000))
                .itemType(Course.ItemType.OWNED)
                .totalQuantity(2)
                .availableQuantity(availableQuantity)
                .instructorId(1L)
                .status(Course.Status.ACTIVE)
                .build();
    }
}
