(define (problem pick_and_place_bottle)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    bottle_1 - bottle
    table_1 counter_1 - surface
  )
  (:init
    (on bottle_1 table_1)
    (reachable robot bottle_1)
    (clear bottle_1)
  )
  (:goal (on bottle_1 counter_1))
)