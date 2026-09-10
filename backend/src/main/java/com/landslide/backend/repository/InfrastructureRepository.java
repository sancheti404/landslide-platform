package com.landslide.backend.repository;

import com.landslide.backend.entity.Infrastructure;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface InfrastructureRepository
        extends JpaRepository<Infrastructure, Long> {

    @Query(value = """
            SELECT *
            FROM infrastructure i
            WHERE ST_DWithin(
                i.location::geography,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                )::geography,
                :distance
            )
            AND (:type IS NULL OR i.type = :type)
            """, nativeQuery = true)
    List<Infrastructure> findNearbyInfrastructure(
            @Param("latitude") Double latitude,
            @Param("longitude") Double longitude,
            @Param("distance") Double distance,
            @Param("type") String type
    );

    @Query("SELECT i.type, COUNT(i) FROM Infrastructure i GROUP BY i.type")
    List<Object[]> countInfrastructureByType();
}

