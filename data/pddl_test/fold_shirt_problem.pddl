(define (problem fold_shirt)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    shirt_1 - shirt
  )
  (:init
    (reachable robot shirt_1)
  )
  (:goal (folded shirt_1))
)