package com.landslide.backend.repository;

import com.landslide.backend.entity.Infrastructure;
import com.landslide.backend.entity.InfrastructureType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface InfrastructureRepository extends JpaRepository<Infrastructure, Long> {

    List<Infrastructure> findByType(InfrastructureType type);

    @Query(value = """
            SELECT *
            FROM infrastructure i
            WHERE ST_DWithin(
                i.location,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                ),
                :distanceInDegrees
            )
            """, nativeQuery = true)
    List<Infrastructure> findInfrastructureNearPoint(
            @Param("latitude") Double latitude,
            @Param("longitude") Double longitude,
            @Param("distanceInDegrees") Double distanceInDegrees
    );
}
