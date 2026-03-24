(define (problem sweep_floor)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    broom_1 - broom
    floor_1 - surface
  )
  (:init
    (holding robot broom_1)
  )
  (:goal (clean floor_1))
)