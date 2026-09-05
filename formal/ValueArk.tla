----------------------------- MODULE ValueArk -----------------------------
EXTENDS Naturals, Sequences

CONSTANT Assets

VARIABLES stage, weights, automaticTradeAuthority, leverageAllowed,
          brokerConnection, specificSecurityRecommendation

Stages == {"INPUT", "ANALYZED", "PROPOSED", "EXPORTED"}

TypeOK ==
  /\ stage \in Stages
  /\ weights \in [Assets -> 0..100]
  /\ automaticTradeAuthority \in {0}
  /\ leverageAllowed \in {FALSE}
  /\ brokerConnection \in {0}
  /\ specificSecurityRecommendation \in {FALSE}

NoAutomaticTrade == automaticTradeAuthority = 0
NoLeverage == leverageAllowed = FALSE
NoBrokerConnection == brokerConnection = 0
NoSpecificSecurity == specificSecurityRecommendation = FALSE
NonNegativeWeights == \A a \in Assets : weights[a] >= 0

Init ==
  /\ stage = "INPUT"
  /\ weights = [a \in Assets |-> 0]
  /\ automaticTradeAuthority = 0
  /\ leverageAllowed = FALSE
  /\ brokerConnection = 0
  /\ specificSecurityRecommendation = FALSE

Analyze ==
  /\ stage = "INPUT"
  /\ stage' = "ANALYZED"
  /\ UNCHANGED <<weights, automaticTradeAuthority, leverageAllowed,
                  brokerConnection, specificSecurityRecommendation>>

Propose ==
  /\ stage = "ANALYZED"
  /\ stage' = "PROPOSED"
  /\ UNCHANGED <<weights, automaticTradeAuthority, leverageAllowed,
                  brokerConnection, specificSecurityRecommendation>>

Export ==
  /\ stage \in {"ANALYZED", "PROPOSED"}
  /\ stage' = "EXPORTED"
  /\ UNCHANGED <<weights, automaticTradeAuthority, leverageAllowed,
                  brokerConnection, specificSecurityRecommendation>>

Next == Analyze \/ Propose \/ Export
Spec == Init /\ [][Next]_<<stage,weights,automaticTradeAuthority,leverageAllowed,brokerConnection,specificSecurityRecommendation>>
=============================================================================
