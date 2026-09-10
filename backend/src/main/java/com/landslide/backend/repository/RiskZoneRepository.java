package com.landslide.backend.repository;

import com.landslide.backend.entity.RiskZone;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RiskZoneRepository extends JpaRepository<RiskZone, Long> {

    @Query(value = """
            SELECT *
            FROM risk_zones rz
            WHERE ST_Contains(
                rz.boundary,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                )
            )
            """, nativeQuery = true)
    List<RiskZone> findRiskZonesContainingPoint(
            @Param("latitude") Double latitude,
            @Param("longitude") Double longitude
    );

    @Query(value = """
            SELECT COUNT(*) > 0
            FROM risk_zones rz
            WHERE ST_Intersects(
                rz.boundary,
                ST_SetSRID(ST_GeomFromText(:boundaryWkt), 4326)
            )
            """, nativeQuery = true)
    boolean existsOverlappingRiskZone(
            @Param("boundaryWkt") String boundaryWkt
    );

    @Query(value = """
            SELECT COUNT(*) > 0
            FROM risk_zones rz
            WHERE rz.id <> :currentId
            AND ST_Intersects(
                rz.boundary,
                ST_SetSRID(ST_GeomFromText(:boundaryWkt), 4326)
            )
            """, nativeQuery = true)
    boolean existsOverlappingRiskZoneExcludingId(
            @Param("boundaryWkt") String boundaryWkt,
            @Param("currentId") Long currentId
    );
}
