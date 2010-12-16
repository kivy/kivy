Widget:

	Scatter:
		pos: 50, 50
		rotation: 45
		scale: 2
		canvas:
			PushMatrix
			Translate:
				xy: -self.width / 2., -self.height / 2.
			Scale:
				scale: self.scale
			Rotate:
				angle: self.rotation
				axis: (0, 0, 1)
			Translate:
				xy: self.width / 2. + self.x, self.height / 2. + self.y

			Color:
				rgb: (self.rotation / 360., 1, 1)
			Rectangle:
				size: self.size
			PopMatrix

