import { NextResponse } from "next/server";
import postgres from "postgres";

const sql = postgres(process.env.DATABASE_URL!, {
  ssl: "require",
});

interface VerifyRequestBody {
  makeVisible?: boolean;
}

/**
 * POST /api/admin/hospitals/[id]/verify
 * Verifies a hospital and optionally makes it visible on the public site.
 * Body: { makeVisible: boolean } (default: true)
 */
export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const hospitalId = params.id;
    const body: VerifyRequestBody = await request.json().catch(() => ({}));
    const makeVisible = body.makeVisible ?? true;

    // Update hospital verification status
    const result = await sql`
      UPDATE hospitals
      SET
        is_verified = true,
        is_visible = ${makeVisible},
        updated_at = NOW()
      WHERE id = ${hospitalId}
      RETURNING *
    `;

    if (result.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Hospital not found",
        },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: result[0],
      message: `Hospital verified and ${makeVisible ? "made visible" : "kept hidden"}`,
    });
  } catch (error) {
    console.error("Failed to verify hospital:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to verify hospital",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/admin/hospitals/[id]/verify
 * Rejects a hospital by deleting it from the database.
 * Use this for hospitals that shouldn't be in the system.
 */
export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const hospitalId = params.id;

    // Delete the hospital
    const result = await sql`
      DELETE FROM hospitals
      WHERE id = ${hospitalId}
      RETURNING id, name
    `;

    if (result.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Hospital not found",
        },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      message: `Hospital "${result[0].name}" rejected and removed from database`,
    });
  } catch (error) {
    console.error("Failed to reject hospital:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to reject hospital",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
