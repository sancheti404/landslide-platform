package com.landslide.backend.repository;

import com.landslide.backend.entity.LandslideEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface LandslideEventRepository
        extends JpaRepository<LandslideEvent, Long> {

}
