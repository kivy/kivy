/*
 * Poly2Tri Copyright (c) 2009-2010, Poly2Tri Contributors
 * http://code.google.com/p/poly2tri/
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 * * Neither the name of Poly2Tri nor the names of its contributors may be
 *   used to endorse or promote products derived from this software without specific
 *   prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
/**
 * Sweep-line, Constrained Delauney Triangulation (CDT) See: Domiter, V. and
 * Zalik, B.(2008)'Sweep-line algorithm for constrained Delaunay triangulation',
 * International Journal of Geographical Information Science
 *
 * "FlipScan" Constrained Edge Algorithm invented by Thomas Åhlén, thahlen@gmail.com
 */

#ifndef SWEEP_H
#define SWEEP_H

#include <vector>

namespace p2t {

class SweepContext;
struct Node;
struct Point;
struct Edge;
class Triangle;

class Sweep {
public:

void Triangulate(SweepContext& tcx);
~Sweep();

private:

void SweepPoints(SweepContext& tcx);

Node& PointEvent(SweepContext& tcx, Point& point);

void EdgeEvent(SweepContext& tcx, Edge* edge, Node* node);

void EdgeEvent(SweepContext& tcx, Point& ep, Point& eq, Triangle* triangle, Point& point);

Node& NewFrontTriangle(SweepContext& tcx, Point& point, Node& node);

void Fill(SweepContext& tcx, Node& node);

bool Legalize(SweepContext& tcx, Triangle& t);

bool Incircle(Point& pa, Point& pb, Point& pc, Point& pd);

void RotateTrianglePair(Triangle& t, Point& p, Triangle& ot, Point& op);

void FillAdvancingFront(SweepContext& tcx, Node& n);

double HoleAngle(Node& node);

double BasinAngle(Node& node);

void FillBasin(SweepContext& tcx, Node& node);

void FillBasinReq(SweepContext& tcx, Node* node);

bool IsShallow(SweepContext& tcx, Node& node);

bool IsEdgeSideOfTriangle(Triangle& triangle, Point& ep, Point& eq);

void FillEdgeEvent(SweepContext& tcx, Edge* edge, Node* node);

void FillRightAboveEdgeEvent(SweepContext& tcx, Edge* edge, Node* node);

void FillRightBelowEdgeEvent(SweepContext& tcx, Edge* edge, Node& node);

void FillRightConcaveEdgeEvent(SweepContext& tcx, Edge* edge, Node& node);

void FillRightConvexEdgeEvent(SweepContext& tcx, Edge* edge, Node& node);

void FillLeftAboveEdgeEvent(SweepContext& tcx, Edge* edge, Node* node);

void FillLeftBelowEdgeEvent(SweepContext& tcx, Edge* edge, Node& node);

void FillLeftConcaveEdgeEvent(SweepContext& tcx, Edge* edge, Node& node);

void FillLeftConvexEdgeEvent(SweepContext& tcx, Edge* edge, Node& node);

void FlipEdgeEvent(SweepContext& tcx, Point& ep, Point& eq, Triangle* t, Point& p);

Triangle& NextFlipTriangle(SweepContext& tcx, int o, Triangle&  t, Triangle& ot, Point& p, Point& op);

Point& NextFlipPoint(Point& ep, Point& eq, Triangle& ot, Point& op);

void FlipScanEdgeEvent(SweepContext& tcx, Point& ep, Point& eq, Triangle& flip_triangle, Triangle& t, Point& p);

void FinalizationPolygon(SweepContext& tcx);

std::vector<Node*> nodes_;

};

}

#endif
