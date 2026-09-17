/**
 * Architectural Service Boundary: Future Multi-Agent AI Orchestrator
 *
 * NOTE: Phase 11 Constraint:
 * Do NOT implement fake agent responses.
 * When the backend AI orchestrator is established, this service will bridge
 * conversational prompts, specialized tool invocation (GIS agent, Evacuation agent, Risk agent),
 * and streaming agent reasoning tokens.
 */

export const AgentApi = {
  isConfigured: () => false,

  sendMessage: async (userPrompt, context = {}) => {
    throw new Error(
      'AI Agent Orchestration service is not yet enabled. Backend multi-agent orchestration architecture is scheduled for future phases.'
    );
  },

  getAvailableAgents: () => [
    {
      id: 'risk-agent',
      name: 'Terrain & Risk Intelligence Agent',
      status: 'PLANNED',
      tools: ['evaluate_coordinates', 'query_dem_features', 'explain_multimodal_fusion'],
    },
    {
      id: 'rainfall-agent',
      name: 'Dynamic Hydrometeorological Agent',
      status: 'PLANNED',
      tools: ['query_chirps_cache', 'calculate_antecedent_stress', 'eval_trigger_indicator'],
    },
    {
      id: 'evacuation-agent',
      name: 'Civil Protection & Routing Agent',
      status: 'PLANNED',
      tools: ['compute_safe_corridors', 'query_nearby_hospitals', 'simulate_bottlenecks'],
    }
  ]
};
