(define (problem pick_cup_from_table)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    cup_1 - cup
    table_1 - surface
  )
  (:init
    (on cup_1 table_1)
    (reachable robot cup_1)
    (clear cup_1)
  )
  (:goal (holding robot cup_1))
)