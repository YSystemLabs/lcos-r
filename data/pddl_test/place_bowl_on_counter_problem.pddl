(define (problem place_bowl_on_counter)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    bowl_1 - bowl
    counter_1 - surface
  )
  (:init
    (holding robot bowl_1)
  )
  (:goal (on bowl_1 counter_1))
)