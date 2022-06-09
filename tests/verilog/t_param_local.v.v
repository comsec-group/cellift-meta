module t (
	a,
	y
);
	input [1:0] a;
	output wire [3:0] y;
	Test #(.C(2)) test(
		.a(a),
		.y(y)
	);
endmodule
module Test (
	a,
	y
);
	parameter C = 3;
	localparam O = 1 << C;
	input [C - 1:0] a;
	output reg [O - 1:0] y;
	initial begin
		if (O != 4)
			$stop;
		$write("*-* All Finished *-*\n");
	end
endmodule
