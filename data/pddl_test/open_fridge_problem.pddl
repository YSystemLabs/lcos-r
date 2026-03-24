(define (problem open_fridge)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    fridge_1 - fridge
  )
  (:init
    (reachable robot fridge_1)
    (closed fridge_1)
  )
  (:goal (open fridge_1))
)