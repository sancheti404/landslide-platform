package com.landslide.backend.dto;

import java.util.List;

public class NearbyInfrastructureResponse {

    private List<InfrastructureResponse> hospitals;
    private List<InfrastructureResponse> shelters;
    private List<InfrastructureResponse> policeStations;
    private List<InfrastructureResponse> roads;

    public NearbyInfrastructureResponse(
            List<InfrastructureResponse> hospitals,
            List<InfrastructureResponse> shelters,
            List<InfrastructureResponse> policeStations,
            List<InfrastructureResponse> roads
    ) {
        this.hospitals = hospitals;
        this.shelters = shelters;
        this.policeStations = policeStations;
        this.roads = roads;
    }

    public List<InfrastructureResponse> getHospitals() {
        return hospitals;
    }

    public List<InfrastructureResponse> getShelters() {
        return shelters;
    }

    public List<InfrastructureResponse> getPoliceStations() {
        return policeStations;
    }

    public List<InfrastructureResponse> getRoads() {
        return roads;
    }
}
