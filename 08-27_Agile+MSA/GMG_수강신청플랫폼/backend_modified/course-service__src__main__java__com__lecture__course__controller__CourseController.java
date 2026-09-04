package com.lecture.course.controller;

import com.lecture.course.dto.CourseDto;
import com.lecture.course.entity.Course;
import com.lecture.course.service.CourseService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/courses")
@RequiredArgsConstructor
public class CourseController {

    private final CourseService courseService;

    @PostMapping
    public ResponseEntity<CourseDto.ApiResponse<CourseDto.CourseResponse>> createCourse(
            @Valid @RequestBody CourseDto.CreateRequest request,
            @RequestHeader("X-User-Id") Long operatorId) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(CourseDto.ApiResponse.success(courseService.createCourse(request, operatorId)));
    }

    @GetMapping
    public ResponseEntity<CourseDto.ApiResponse<List<CourseDto.CourseResponse>>> getAllCourses(
            @RequestHeader(value = "X-User-Id", required = false) Long userId,
            @RequestParam(required = false) Long groupId) {
        return ResponseEntity.ok(CourseDto.ApiResponse.success(
                courseService.getAllCourses(userId, groupId)
        ));
    }

    @GetMapping("/{id}")
    public ResponseEntity<CourseDto.ApiResponse<CourseDto.CourseResponse>> getCourse(
            @PathVariable Long id,
            @RequestHeader(value = "X-User-Id", required = false) Long userId) {
        return ResponseEntity.ok(CourseDto.ApiResponse.success(
                courseService.getCourseForUser(id, userId)
        ));
    }

    @GetMapping("/category/{category}")
    public ResponseEntity<CourseDto.ApiResponse<List<CourseDto.CourseResponse>>> getCoursesByCategory(
            @PathVariable Course.Category category,
            @RequestHeader(value = "X-User-Id", required = false) Long userId,
            @RequestParam(required = false) Long groupId) {
        return ResponseEntity.ok(CourseDto.ApiResponse.success(
                courseService.getCoursesByCategory(category, userId, groupId)
        ));
    }

    @GetMapping("/internal/exists/{id}")
    public ResponseEntity<Boolean> existsCourse(@PathVariable Long id) {
        return ResponseEntity.ok(courseService.existsCourse(id));
    }

    @GetMapping("/internal/{id}")
    public ResponseEntity<CourseDto.CourseResponse> getCourseInternal(@PathVariable Long id) {
        return ResponseEntity.ok(courseService.getCourse(id));
    }

    @GetMapping("/internal/analytics/assets")
    public ResponseEntity<List<CourseDto.CourseResponse>> getAssetsForAnalytics() {
        return ResponseEntity.ok(courseService.getAllAssetsInternal());
    }

    @PostMapping("/internal/acquisition-requests")
    public ResponseEntity<CourseDto.CourseResponse> createAcquisitionRequest(
            @Valid @RequestBody CourseDto.InternalAcquisitionRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(courseService.createAcquisitionRequest(request));
    }

    @PostMapping("/internal/{id}/enrollment-count")
    public ResponseEntity<Void> increaseEnrollmentCount(@PathVariable Long id) {
        courseService.increaseEnrollmentCount(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/internal/{id}/borrow")
    public ResponseEntity<Void> borrowCourse(@PathVariable Long id) {
        courseService.borrowCourse(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/internal/{id}/return")
    public ResponseEntity<Void> returnCourse(@PathVariable Long id) {
        courseService.returnCourse(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/internal/{id}/receive")
    public ResponseEntity<CourseDto.CourseResponse> receiveCourse(
            @PathVariable Long id,
            @Valid @RequestBody CourseDto.ReceiveRequest request) {
        return ResponseEntity.ok(courseService.receiveCourse(id, request));
    }

    @GetMapping("/internal/recommend")
    public ResponseEntity<List<CourseDto.CourseResponse>> getRecommendCourses(
            @RequestParam Course.Category category,
            @RequestParam(defaultValue = "") List<Long> excludeIds) {
        return ResponseEntity.ok(courseService.getRecommendCourses(category, excludeIds));
    }
}
