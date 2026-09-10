package com.landslide.backend.repository;

import com.landslide.backend.entity.LandslideEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface LandslideEventRepository
        extends JpaRepository<LandslideEvent, Long> {

    @Modifying
    @Query("UPDATE LandslideEvent l SET l.riskZone = null WHERE l.riskZone.id = :riskZoneId")
    void detachRiskZoneFromLandslides(@Param("riskZoneId") Long riskZoneId);
}
