package com.landslide.backend.repository;

import com.landslide.backend.entity.Infrastructure;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface InfrastructureRepository
        extends JpaRepository<Infrastructure, Long> {

}
